cmake_minimum_required(VERSION 3.16)
            project(WindFlowGeneratedQueries CXX)

            set(CMAKE_CXX_STANDARD 17)
            set(CMAKE_CXX_STANDARD_REQUIRED ON)
            set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -DNDEBUG")

            find_package(Threads REQUIRED)

            include_directories(
                "/home/user/TableAPI/include"
    "/home/user/TableAPI/include/WindFlow/wf"
    "/home/user/TableAPI/include/fastflow"
    "/home/user/TableAPI/include/Table_WindFlow"
    "/home/user/TableAPI/examples/self_interval_join_output"
            )
            
            # --- Target per Query: self_interval_join ---
            add_executable(self_interval_join self_interval_join_main.cpp)
            target_link_libraries(self_interval_join PRIVATE Threads::Threads pthread)
            