
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
    "/home/user/TableAPI/nexmark_queries/query5"
)
            
# --- Target per Query: auctions_with_max_bids ---
add_executable(auctions_with_max_bids auctions_with_max_bids_main.cpp)
target_link_libraries(auctions_with_max_bids PRIVATE Threads::Threads pthread)
