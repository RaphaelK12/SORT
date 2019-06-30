#    This file is a part of SORT(Simple Open Ray Tracing), an open-source cross
#    platform physically based renderer.
#
#    Copyright (c) 2011-2019 by Cao Jiayin - All rights reserved.
#
#    SORT is a free software written for educational purpose. Anyone can distribute
#    or modify it under the the terms of the GNU General Public License Version 3 as
#    published by the Free Software Foundation. However, there is NO warranty that
#    all components are functional in a perfect manner. Without even the implied
#    warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#    General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along with
#    this program. If not, see <http://www.gnu.org/licenses/gpl-3.0.html>.

import bpy
from ..material import nodes
from ..material import properties
from .. import base
from bl_ui import properties_data_camera

class SORTMaterialPanel:
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    COMPAT_ENGINES = {'SORT'}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine in cls.COMPAT_ENGINES

class SORTMaterialPreview(SORTMaterialPanel, bpy.types.Panel):
    bl_label = "Preview"
    bl_context = "material"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.material and SORTMaterialPanel.poll(context)

    def draw(self, context):
        self.layout.template_preview(context.material)

class SORT_Add_Node:
    def get_type_items(cls, context):
        items = []
        for category , types in nodes.SORTPatternGraph.nodetypes.items():
            found_item = False
            for type in types:
                if properties.isCompatible( type[3] , cls.socket_type ):
                #if type[3] == cls.socket_type:
                    found_item = True
                    break
            if found_item is False:
                continue
            items.append(('', category, ''))
            for type in types:
                if properties.isCompatible( type[3] , cls.socket_type ):
                #if type[3] == cls.socket_type:
                    items.append(( type[0] + '#' + type[2] , type[1] , type[2] ))
        if cls.connected:
            items.append(('', 'Link', ''))
            items.append(('REMOVE', 'Remove', 'Remove the node connected to this socket'))
            items.append(('DISCONNECT', 'Disconnect', 'Disconnect the node connected to this socket'))
        return items

    node_type : bpy.props.EnumProperty(name="Node Type", description='Node type to add to this socket', items=get_type_items)

    def execute(self, context):
        encoded = self.properties.node_type
        decoded = encoded.split('#')
        new_type = decoded[0]
        # socket to connect, some nodes have multiple sockets that match the source socket type
        tc_socket = decoded[1] if len(decoded) > 1 else None
        if new_type == 'DEFAULT':
            return {'CANCELLED'}

        nt = context.nodetree
        node = context.node
        socket = context.socket
        def socket_node_input(nt, socket):
            return next((l.from_node for l in nt.links if l.to_socket == socket), None)
        input_node = socket_node_input(nt, socket)

        if new_type == 'REMOVE':
            if input_node is not None:
                nt.nodes.remove(input_node)
            return {'FINISHED'}

        if new_type == 'DISCONNECT':
            link = next((l for l in nt.links if l.to_socket == socket), None)
            if link is not None:
                nt.links.remove(link)
            return {'FINISHED'}

        if input_node is None:
            # add a new node to existing socket
            newnode = nt.nodes.new(new_type)
            newnode.update_ui_from_output(tc_socket)
            newnode.location = node.location
            newnode.location[0] -= 300
            newnode.selected = False
            nt.links.new(newnode.outputs[tc_socket], socket)
        else:
            # replace input node with a new one
            newnode = nt.nodes.new(new_type)
            newnode.update_ui_from_output(tc_socket)
            old_node = socket.links[0].from_node
            nt.links.new(newnode.outputs[tc_socket], socket)
            newnode.location = old_node.location

            nt.nodes.remove(old_node)
        return {'FINISHED'}

@base.register_class
class NODE_OT_add_surface_SORTNodeSocketBxdf(bpy.types.Operator, SORT_Add_Node):
    bl_idname = 'node.add_surface_sortnodesocketbxdf'
    bl_label = 'Add Bxdf Node'
    bl_description = 'Connect a node to this socket'
    socket_type : bpy.props.StringProperty(default='SORTNodeSocketBxdf')
    connected : bpy.props.BoolProperty(default=True)

@base.register_class
class NODE_OT_add_surface_SORTNodeSocketColor(bpy.types.Operator, SORT_Add_Node):
    bl_idname = 'node.add_surface_sortnodesocketcolor'
    bl_label = 'Add Color Node'
    bl_description = 'Connect a node to this socket'
    socket_type : bpy.props.StringProperty(default='SORTNodeSocketColor')
    connected : bpy.props.BoolProperty(default=True)

@base.register_class
class NODE_OT_add_surface_SORTNodeSocketFloat(bpy.types.Operator, SORT_Add_Node):
    bl_idname = 'node.add_surface_sortnodesocketfloat'
    bl_label = 'Add Float Node'
    bl_description = 'Connect a node to this socket'
    socket_type : bpy.props.StringProperty(default='SORTNodeSocketFloat')
    connected : bpy.props.BoolProperty(default=True)

@base.register_class
class NODE_OT_add_surface_SORTNodeSocketLargeFloat(bpy.types.Operator, SORT_Add_Node):
    bl_idname = 'node.add_surface_sortnodesocketlargefloat'
    bl_label = 'Add Bxdf Node'
    bl_description = 'Connect a node to this socket'
    socket_type : bpy.props.StringProperty(default='SORTNodeSocketLargeFloat')
    connected : bpy.props.BoolProperty(default=True)

@base.register_class
class NODE_OT_add_surface_SORTNodeSocketNormal(bpy.types.Operator, SORT_Add_Node):
    bl_idname = 'node.add_surface_sortnodesocketnormal'
    bl_label = 'Add Bxdf Node'
    bl_description = 'Connect a node to this socket'
    socket_type : bpy.props.StringProperty(default='SORTNodeSocketNormal')
    connected : bpy.props.BoolProperty(default=True)

@base.register_class
class NODE_OT_add_surface_SORTNodeSocketBxdf_NoRemove(bpy.types.Operator, SORT_Add_Node):
    bl_idname = 'node.add_surface_sortnodesocketbxdf_no_remove'
    bl_label = 'Add Bxdf Node'
    bl_description = 'Connect a node to this socket'
    socket_type : bpy.props.StringProperty(default='SORTNodeSocketBxdf')
    connected : bpy.props.BoolProperty(default=False)

@base.register_class
class NODE_OT_add_surface_SORTNodeSocketColor_NoRemove(bpy.types.Operator, SORT_Add_Node):
    bl_idname = 'node.add_surface_sortnodesocketcolor_no_remove'
    bl_label = 'Add Color Node'
    bl_description = 'Connect a node to this socket'
    socket_type : bpy.props.StringProperty(default='SORTNodeSocketColor')
    connected : bpy.props.BoolProperty(default=False)

@base.register_class
class NODE_OT_add_surface_SORTNodeSocketFloat_NoRemove(bpy.types.Operator, SORT_Add_Node):
    bl_idname = 'node.add_surface_sortnodesocketfloat_no_remove'
    bl_label = 'Add Float Node'
    bl_description = 'Connect a node to this socket'
    socket_type : bpy.props.StringProperty(default='SORTNodeSocketFloat')
    connected : bpy.props.BoolProperty(default=False)

@base.register_class
class NODE_OT_add_surface_SORTNodeSocketLargeFloat_NoRemove(bpy.types.Operator, SORT_Add_Node):
    bl_idname = 'node.add_surface_sortnodesocketlargefloat_no_remove'
    bl_label = 'Add Bxdf Node'
    bl_description = 'Connect a node to this socket'
    socket_type : bpy.props.StringProperty(default='SORTNodeSocketLargeFloat')
    connected : bpy.props.BoolProperty(default=False)

@base.register_class
class NODE_OT_add_surface_SORTNodeSocketNormal_NoRemove(bpy.types.Operator, SORT_Add_Node):
    bl_idname = 'node.add_surface_sortnodesocketnormal_no_remove'
    bl_label = 'Add Bxdf Node'
    bl_description = 'Connect a node to this socket'
    socket_type : bpy.props.StringProperty(default='SORTNodeSocketNormal')
    connected : bpy.props.BoolProperty(default=False)

@base.register_class
class NODE_OT_add_surface_sortnodesocketuv(bpy.types.Operator, SORT_Add_Node):
    bl_idname = 'node.add_surface_sortnodesocketuv'
    bl_label = 'Add UV Mapping Node'
    bl_description = 'Connect a node to this socket'
    socket_type : bpy.props.StringProperty(default='SORTNodeUVMapping')
    connected : bpy.props.BoolProperty(default=False)

@base.register_class
class NODE_OT_add_surface_sortnodesocketuv_no_remove(bpy.types.Operator, SORT_Add_Node):
    bl_idname = 'node.add_surface_sortnodesocketuv_no_remove'
    bl_label = 'Add UV Mapping Node'
    bl_description = 'Connect a node to this socket'
    socket_type : bpy.props.StringProperty(default='SORTNodeUVMapping')
    connected : bpy.props.BoolProperty(default=False)

@base.register_class
class NODE_OP_add_surface_sortnodesocketfloatvector(bpy.types.Operator, SORT_Add_Node):
    bl_idname = 'node.add_surface_sortnodesocketfloatvector'
    bl_label = 'Add Vector Node'
    bl_description = 'Connect a node to this socket'
    socket_type : bpy.props.StringProperty(default='SORTNodeSocketFloatVector')
    connected : bpy.props.BoolProperty(default=False)

@base.register_class
class NODE_OP_add_surface_sortnodesocketfloatvector_no_remove(bpy.types.Operator, SORT_Add_Node):
    bl_idname = 'node.add_surface_sortnodesocketfloatvector_no_remove'
    bl_label = 'Add Vector Node'
    bl_description = 'Connect a node to this socket'
    socket_type : bpy.props.StringProperty(default='SORTNodeSocketFloatVector')
    connected : bpy.props.BoolProperty(default=False)

@base.register_class
class NODE_OP_add_surface_sortnodesocketanyfloat(bpy.types.Operator, SORT_Add_Node):
    bl_idname = 'node.add_surface_sortnodesocketanyfloat'
    bl_label = 'Add Float Node'
    bl_description = 'Connect a node to this socket'
    socket_type : bpy.props.StringProperty(default='SORTNodeSocketFloatVector')
    connected : bpy.props.BoolProperty(default=False)

@base.register_class
class NODE_OP_add_surface_sortnodesocketanyfloat_no_remove(bpy.types.Operator, SORT_Add_Node):
    bl_idname = 'node.add_surface_sortnodesocketanyfloat_no_remove'
    bl_label = 'Add Float Node'
    bl_description = 'Connect a node to this socket'
    socket_type : bpy.props.StringProperty(default='SORTNodeSocketAnyFloat')
    connected : bpy.props.BoolProperty(default=False)

@base.register_class
class MATERIAL_PT_MaterialSlotPanel(SORTMaterialPanel, bpy.types.Panel):
    bl_label = 'Material Slot'

    def draw(self, context):
        layout = self.layout

        mat = context.material
        ob = context.object
        slot = context.material_slot
        space = context.space_data

        if ob:
            row = layout.row()
            row.template_list("MATERIAL_UL_matslots", "", ob, "material_slots", ob, "active_material_index", rows=4)
            col = row.column(align=True)
            col.operator("object.material_slot_add", icon='ADD', text="")
            col.operator("object.material_slot_remove", icon='REMOVE', text="")
            if ob.mode == 'EDIT':
                row = layout.row(align=True)
                row.operator("object.material_slot_assign", text="Assign")
                row.operator("object.material_slot_select", text="Select")
                row.operator("object.material_slot_deselect", text="Deselect")
        split = layout.split(factor=0.75)
        if ob:
            split.template_ID(ob, "active_material", new="material.new")
            row = split.row()
            if slot:
                row.prop(slot, "link", text="")
            else:
                row.label()
        elif mat:
            split.template_ID(space, "pin_id")
            split.separator()

@base.register_class
class SORT_use_shading_nodes(bpy.types.Operator):
    """Enable nodes on a material, world or lamp"""
    bl_idname = "sort.use_shading_nodes"
    bl_label = "Use Nodes"
    idtype : bpy.props.StringProperty(name="ID Type", default="material")

    def execute(self, context):
        context.material.sort_material = bpy.data.node_groups.new(context.material.name, type='SORTPatternGraph')
        context.material.sort_material.use_fake_user = True
        output = context.material.sort_material.nodes.new('SORTNodeOutput')
        default = context.material.sort_material.nodes.new('SORTNode_Material_Diffuse')
        output.location[0] += 200
        output.location[1] += 200
        default.location[1] += 200
        context.material.sort_material.links.new(default.outputs[0], output.inputs[0])
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        for node in context.material.node_tree.nodes:
            if node.bl_idname == 'SORTNodeOutput':
                return False
        return True

@base.register_class
class MATERIAL_PT_SORTMaterialInstance(SORTMaterialPanel, bpy.types.Panel):
    bl_label = "Surface"

    @classmethod
    def poll(cls, context):
        return context.material and SORTMaterialPanel.poll(context)

    def draw(self, context):
        nt = context.material.sort_material

        # find the output node, duplicated code, to be cleaned
        def find_output_node(ntree):
            if ntree is None:
                return None
            for node in ntree.nodes:
                if getattr(node, "bl_idname", None) == 'SORTNodeOutput':
                    return node
            return None

        output_node = find_output_node(nt)
        if output_node is None:
            self.layout.operator("sort.use_shading_nodes", icon='NODETREE')
            return

        # This panel is close to useless and it is to be deprecated in the future.
        return
        
        socket = output_node.inputs['Surface']
        self.layout.context_pointer_set("nodetree", context.material.node_tree)
        self.layout.context_pointer_set("node", output_node)
        self.layout.context_pointer_set("socket", socket)

        if output_node is not None:
            self.draw_node_properties_recursive(self.layout, context, nt, output_node)

    def draw_node_properties_recursive(self,layout, context, nt, node, level=0):
        def indented_label(layout):
            for i in range(level):
                layout.label(text='',icon='BLANK1')

        layout.context_pointer_set("nodetree", nt)
        layout.context_pointer_set("node", node)

        # draw socket property in panel
        def draw_props(node, layout):
            # node properties
            node.draw_props(context,layout,indented_label)

            # inputs
            for socket in node.inputs:
                layout.context_pointer_set("socket", socket)

                if socket.is_linked:
                    def socket_node_input(nt, socket):
                        return next((l.from_node for l in nt.links if l.to_socket == socket), None)
                    input_node = socket_node_input(nt, socket)
                    if input_node is None:
                        return
                    ui_open = socket.ui_open
                    icon = 'DISCLOSURE_TRI_DOWN' if ui_open else 'DISCLOSURE_TRI_RIGHT'
                    split = layout.split(factor=0.3)
                    row = split.row()
                    indented_label(row)
                    row.prop(socket, "ui_open", icon=icon, text='', icon_only=True, emboss=False)
                    row.label(text=socket.name+":")
                    split.operator_menu_enum("node.add_surface_" + socket.bl_idname.lower() , "node_type", text=input_node.bl_idname , icon= 'DOT')
                    if socket.ui_open:
                        self.draw_node_properties_recursive(layout, context, nt, input_node, level=level+1)
                else:
                    split = layout.split(factor=0.3)
                    row = split.row()
                    indented_label(row)
                    row.label(text=socket.name)
                    prop_panel = split.row( align=True )
                    if socket.default_value is not None:
                        prop_panel.prop(socket,'default_value',text="")
                    prop_panel.operator_menu_enum("node.add_surface_" + socket.bl_idname.lower() + "_no_remove" , "node_type", text='',icon='DOT')

        draw_props(node, layout)
        layout.separator()