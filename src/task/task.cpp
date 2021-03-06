/*
    This file is a part of SORT(Simple Open Ray Tracing), an open-source cross
    platform physically based renderer.

    Copyright (c) 2011-2020 by Jiayin Cao - All rights reserved.

    SORT is a free software written for educational purpose. Anyone can distribute
    or modify it under the the terms of the GNU General Public License Version 3 as
    published by the Free Software Foundation. However, there is NO warranty that
    all components are functional in a perfect manner. Without even the implied
    warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License along with
    this program. If not, see <http://www.gnu.org/licenses/gpl-3.0.html>.
 */

#include "task.h"
#include "core/sassert.h"
#include "core/profile.h"

thread_local static const Task* g_currentTask = nullptr;

class UpdateCurrentTaskWrapper{
public:
    //! Update current task
    UpdateCurrentTaskWrapper( const Task* task ){
        g_currentTask = task;
    }

    //! There is no current on-going task any more.
    ~UpdateCurrentTaskWrapper(){
        g_currentTask = nullptr;
    }
};

void Task::ExecuteTask(){
    SORT_PROFILE(m_name);

    {
        UpdateCurrentTaskWrapper uctw( this );

        // Execute the task.
        Execute();
    }

    // Upon termination of a task, release its dependents' dependencies on this task.
    Scheduler::GetSingleton().TaskFinished( this );
}

// Compare tasks based on its priority, tasks with higher priority get executed earlier.
Scheduler::Task_Comp Scheduler::task_comp = []( const Task* t0 , const Task* t1 ){
    return t0->GetPriority() < t1->GetPriority();
};

Task* Scheduler::Schedule( std::unique_ptr<Task> task ){
    if(IS_PTR_INVALID(task))
        return nullptr;

    std::lock_guard<std::mutex> lock(m_mutex);

    auto taskID = task->GetTaskID();
    m_tasks[taskID] = std::move(task);

    const auto task_ptr = m_tasks[taskID].get();
    if(task_ptr->NoDependency() )
        m_availbleTasks.push(task_ptr);
    else{
        auto dependencies = task_ptr->GetDependencies();
        for (auto dep : dependencies) {
            auto no_const_dep = const_cast<Task*>(dep);
            no_const_dep->AddDependent(task_ptr);
        }
        m_backupTasks.insert(task_ptr);
    }
    return task_ptr;
}

Task* Scheduler::PickTask(){
    std::unique_lock<std::mutex> lock(m_mutex);

    // Wait until this is at least one available task
    while( !( (m_backupTasks.empty() && m_availbleTasks.empty()) || m_availbleTasks.size() ) )
        m_cv.wait_for( lock , std::chrono::seconds(1) );

    // Return nullptr if there is no task available in the scheduler
    if (m_backupTasks.empty() && m_availbleTasks.empty())
        return nullptr;

    // Get the available task that is with highest priority
    Task* ret = m_availbleTasks.top();
    m_availbleTasks.pop();
    return ret;
}

void Scheduler::TaskFinished( const Task* task ){
    std::lock_guard<std::mutex> lock(m_mutex);

    // Starting remove all dependencies.
    const auto& dependent = task->GetDependents();
    for( auto dep : dependent ){
        // Remove its dependencies.
        dep->RemoveDependency( task );

        // There is no dependent task of this 'dep' task anymore, push it into the heap and remove it from the backup tasks.
        if( dep->NoDependency() ){
            m_backupTasks.erase( dep );
            m_availbleTasks.push( dep );

            // Notify one waiting thread to pick up task.
            m_cv.notify_one();
        }
    }

    m_tasks.erase(task->GetTaskID());
}

void    EXECUTING_TASKS(){
    while( true ){
        // Pick a task that is available.
        auto task = Scheduler::GetSingleton().PickTask();

        // If there is no task to be picked, break out of the loop.
        if(IS_PTR_INVALID(task))
            return;

        // Execute the task.
        task->ExecuteTask();
    }
}

const Task* GetCurrentTask(){
    return g_currentTask;
}