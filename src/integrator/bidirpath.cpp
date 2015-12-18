/*
   FileName:      bidirpath.cpp

   Created Time:  2011-09-03 10:18:18

   Auther:        Cao Jiayin

   Email:         soraytrace@hotmail.com

   Location:      China, Shanghai

   Description:   SORT is short for Simple Open-source Ray Tracing. Anyone could checkout the source code from
                'sourceforge', https://soraytrace.svn.sourceforge.net/svnroot/soraytrace. And anyone is free to
                modify or publish the source code. It's cross platform. You could compile the source code in 
                linux and windows , g++ or visual studio 2008 is required.
*/

#include "sort.h"
#include "bidirpath.h"
#include "geometry/scene.h"
#include "light/light.h"
#include "bsdf/bsdf.h"
#include "integratormethod.h"

IMPLEMENT_CREATOR( BidirPathTracing );

// return the radiance of a specific direction
Spectrum BidirPathTracing::Li( const Ray& ray , const PixelSample& ps ) const
{
	// pick a light randomly
	float pdf;
	const Light* light = scene.SampleLight( ps.light_sample[0].t , &pdf );
	if( light == 0 || pdf == 0.0f )
		return 0.0f;

	float	light_pdf = 0.0f;
	Ray		light_ray;
	Vector	n;
	Spectrum le = light->sample_l( ps.light_sample[0] , light_ray , n , &light_pdf );
	le *= 1.0f / pdf ;

	// the path from light and eye
	vector<BDPT_Vertex> light_path , eye_path;

	// generate path from eye
	unsigned eps = _generatePath( ray , 1.0f , eye_path , path_per_pixel , true );
	if( eps == 0 )	return scene.Le( ray );
	// generate path from light
	unsigned lps = _generatePath( light_ray , light_pdf , light_path , path_per_pixel , false );

	//float* total_pdf = SORT_MALLOC_ARRAY( float , eye_path.size() + light_path.size() + 1 );
	//_GeneratePDFSummuration( eye_path, light_path, total_pdf );

	//float* total_pdf2 = SORT_MALLOC_ARRAY( float , eye_path.size() + light_path.size() + 1 );
	//_GeneratePDFSummurationUniform( eye_path, light_path, total_pdf2 );

	// the light intersection
	BDPT_Vertex light_inter;
	light_inter.p = light_ray.m_Ori;
	light_inter.n = n;
	light_inter.pdf = light_pdf;

	Spectrum directWt = 1.0f / pdf;
	Spectrum li;
	for( unsigned i = 1 ; i <= eps ; ++i )
	{
		const BDPT_Vertex& vert = eye_path[i-1];
		directWt /= vert.pdf * vert.rr;
		if( directWt.IsBlack() == false )
		{
			li += directWt * EvaluateDirect( Ray( Point() , -vert.wi ) , scene , light , vert.inter , LightSample(true) , BsdfSample(true) )
				* _Weight( eye_path , i , light_path , 0  );
		}
		directWt *= vert.bsdf->f( vert.wi , vert.wo ) * SatDot( vert.wo , vert.n );

		// connect light sample first
		li += _ConnectLight(vert, light_inter);
		
		for( unsigned j = 1 ; j <= lps ; ++j )
		{
			li += le * _evaluatePath( eye_path , i , light_path , j ) * _Weight( eye_path , i , light_path , j );
		}
	}

	return li + eye_path[0].inter.Le( -ray.m_Dir );
}

// request samples
void BidirPathTracing::RequestSample( Sampler* sampler , PixelSample* ps , unsigned ps_num )
{
	for( unsigned i = 0 ; i < ps_num ; i++ )
	{
		ps[i].bsdf_sample = new BsdfSample[ 1 ];
		ps[i].light_sample = new LightSample[ 1 ];
	}
	ps[0].data = new float[ ps_num * 3 ];
}

// generate samples
void BidirPathTracing::GenerateSample( const Sampler* sampler , PixelSample* samples , unsigned ps , const Scene& scene ) const
{
	Integrator::GenerateSample( sampler , samples , ps , scene );

	if( sampler->RoundSize( ps ) == ps && false )
	{
		float* data_1d = samples[0].data;
		float* data_2d = samples[0].data + ps;

		sampler->Generate1D( data_1d , ps );
		sampler->Generate2D( data_2d , ps );
		const unsigned* shuffled_id0 = ShuffleIndex( ps );

		for( unsigned k = 0 ; k < ps ; ++k )
		{
			int two_k = 2*shuffled_id0[k];
			samples[k].bsdf_sample[0].t = data_1d[two_k];
			samples[k].bsdf_sample[0].u = data_2d[two_k];
			samples[k].bsdf_sample[0].v = data_2d[two_k+1];
		}

		const unsigned* shuffled_id1 = ShuffleIndex( ps );
		sampler->Generate1D( data_1d , ps );
		sampler->Generate2D( data_2d , ps );
		for( unsigned k = 0 ; k < ps ; ++k )
		{
			int two_k = 2*shuffled_id1[k];
			samples[k].light_sample[0].t = data_1d[two_k];
			samples[k].light_sample[0].u = data_2d[two_k];
			samples[k].light_sample[0].v = data_2d[two_k+1];
		}
	}else
	{
		for (unsigned k = 0; k < ps; ++k) 
		{
			samples[k].bsdf_sample[0] = BsdfSample(true);
			samples[k].light_sample[0] = LightSample(true);
		}
	}
}

// output log information
void BidirPathTracing::OutputLog() const
{
	LOG_HEADER( "Integrator" );
	LOG<<"Integrator algorithm : Bidirectional Path Tracing."<<ENDL;
	LOG<<"It supports all of the features in direct lighting algorithm."<<ENDL;
	LOG<<"Some global illumination effect is also supported in path tracing."<<ENDL;
	LOG<<"While it requires much more samples to reduce the noise to an acceptable level."<<ENDL;
	LOG<<"Bidirectional Path Tracing trace rays from eye and light source at the same time."<<ENDL;
}

// generate path
unsigned BidirPathTracing::_generatePath( const Ray& ray , float base_pdf , vector<BDPT_Vertex>& path , unsigned max_vert, bool eye_path ) const
{
	Ray wi = ray;
	Ray wo;
	float pdf = base_pdf;
	float accu_pdf = 1.0f;
	Spectrum accu_radiance = 1.0f;
	while( path.size() < max_vert )
	{
		BDPT_Vertex vert;
		if( false == scene.GetIntersect( wi , &vert.inter ) )
			break;
		
		vert.p = vert.inter.intersect;
		vert.n = vert.inter.normal;
		vert.pri = vert.inter.primitive;
		vert.wi = -wi.m_Dir;
		vert.pdf = pdf;
		vert.bsdf = vert.inter.primitive->GetMaterial()->GetBsdf(&vert.inter);
		
		if (path.size() > 4 )
		{
			if ( sort_canonical() > 0.5f)
				break;
			else
			{
				accu_pdf *= 0.5f;
				vert.rr = 0.5f;
			}
		}

		accu_pdf *= pdf;
		vert.accu_pdf = accu_pdf;

		Spectrum bsdf_value = vert.bsdf->sample_f( vert.wi , vert.wo , BsdfSample(true) , &pdf );
		accu_radiance *= bsdf_value * AbsDot(vert.wo, vert.n);
		vert.accu_radiance = accu_radiance;

		if (pdf == 0 || bsdf_value.IsBlack())
			return path.size();

		path.push_back( vert );

		wi = Ray( vert.inter.intersect , vert.wo , 0 , 0.001f );
	}

	return path.size();
}

// evaluate path
Spectrum BidirPathTracing::_evaluatePath(const vector<BDPT_Vertex>& epath , int esize , 
										const vector<BDPT_Vertex>& lpath , int lsize ) const
{
	if( lpath.empty() )
		return 0.0f;

	Spectrum radiance = (esize > 1) ? epath[esize - 2].accu_radiance : 1.0f;
	Spectrum weight = (lsize > 1) ? lpath[lsize - 2].accu_radiance : 1.0f;
	const BDPT_Vertex& evert = epath[esize-1];
	const BDPT_Vertex& lvert = lpath[lsize-1];
	Spectrum li = radiance * weight * _Gterm(evert, lvert) / (evert.accu_pdf * lvert.accu_pdf);
	return li;
}

// compute G term
Spectrum BidirPathTracing::_Gterm( const BDPT_Vertex& p0 , const BDPT_Vertex& p1 ) const
{
	Vector delta = p0.p - p1.p;
	Vector n_delta = Normalize(delta);

	Spectrum g = AbsDot( p0.n , -n_delta ) * p1.bsdf->f( p1.wi , n_delta ) * p0.bsdf->f( -n_delta, p0.wi ) * AbsDot( p1.n , n_delta ) / delta.SquaredLength();
	if( g.IsBlack() )
		return 0.0f;

	Visibility visible( scene );
	visible.ray = Ray( p1.p , n_delta  , 0 , 0.1f , delta.Length() - 0.1f );
	if( visible.IsVisible() == false )
		return 0.0f;
	
	return g;
}

// weight the path
float BidirPathTracing::_Weight(const vector<BDPT_Vertex>& epath , int esize , 
								const vector<BDPT_Vertex>& lpath , int lsize ) const
{
	return 1.0f / (esize + lsize);
	/*float pdf = epath[esize-1].accu_pdf;
	if( lsize > 0 )
		pdf *= lpath[lsize-1].accu_pdf;
	return 1.0f / total_pdf_uniform[esize+lsize];
	//return _pdf;
	return pdf / total_pdf[esize+lsize];*/
}
/*
// generate summeration of pdf
void BidirPathTracing::_GeneratePDFSummuration( const vector<BDPT_Vertex>& epath , const vector<BDPT_Vertex>& lpath , float* result ) const
{
	unsigned eps = epath.size();
	unsigned lps = lpath.size();

	for(unsigned i = 0; i < eps + lps + 1 ; ++i )
		result[i] = 0.0f;
	for( unsigned i = 1 ; i <= eps ; ++i )
	{
		result[i] += epath[i-1].accu_pdf;
		for( unsigned j = 1 ; j <= lps ; ++j )
			result[i+j] += epath[i-1].accu_pdf * lpath[j-1].accu_pdf;
	}
}

// generate summeration of pdf
void BidirPathTracing::_GeneratePDFSummurationUniform( const vector<BDPT_Vertex>& epath , const vector<BDPT_Vertex>& lpath , float* result ) const
{
	unsigned eps = epath.size();
	unsigned lps = lpath.size();

	for(unsigned i = 0; i < eps + lps + 1 ; ++i )
		result[i] = 0.0f;
	for( unsigned i = 1 ; i <= eps ; ++i )
	{
		result[i]++;
		for( unsigned j = 1 ; j <= lps ; ++j )
			result[i+j]++;
	}
}*/

// connect light sample
Spectrum BidirPathTracing::_ConnectLight(const BDPT_Vertex& eye_vertex, const BDPT_Vertex& light_vertex) const
{
/*	if (lpath.empty())
		return 0.0f;

	Spectrum li(1.0f);

	for (int i = 0; i < esize - 1; ++i)
	{
		const BDPT_Vertex& vert = epath[i];
		li *= vert.bsdf->f(vert.wi, vert.wo) * SatDot(vert.wo, vert.n);// / ( vert.pdf * vert.rr );
	}

	for (int i = 0; i < lsize - 1; ++i)
	{
		const BDPT_Vertex& vert = lpath[i];
		li *= vert.bsdf->f(vert.wo, vert.wi) * SatDot(vert.wi, vert.n);// / ( vert.pdf * vert.rr );
	}

	const BDPT_Vertex& evert = epath[esize - 1];
	const BDPT_Vertex& lvert = lpath[lsize - 1];
	li *= _Gterm(evert, lvert) / (evert.accu_pdf * lvert.accu_pdf);//( evert.pdf * lvert.pdf * evert.rr * lvert.rr);
	*/
	return 0.0f;
}