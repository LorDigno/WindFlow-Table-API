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
    "/home/user/TableAPI/examples/avg_cold_temperature_output"
            )
            
            # --- Target per Query: avg_cold_temperature ---
            add_executable(avg_cold_temperature avg_cold_temperature_main.cpp)
            target_link_libraries(avg_cold_temperature PRIVATE Threads::Threads pthread)
            