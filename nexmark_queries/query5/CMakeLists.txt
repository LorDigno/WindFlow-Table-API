
cmake_minimum_required(VERSION 3.16)
project(WindFlowGeneratedQueries CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -DNDEBUG")

find_package(Threads REQUIRED)

include_directories(
    "/disc1/homes/lorenzoni/WindFlow-Table-API/include"
    "/disc1/homes/lorenzoni/WindFlow-Table-API/include/WindFlow/wf"
    "/disc1/homes/lorenzoni/WindFlow-Table-API/include/fastflow"
    "/disc1/homes/lorenzoni/WindFlow-Table-API/include/Table_WindFlow"
    "/disc1/homes/lorenzoni/WindFlow-Table-API/nexmark_queries/query5"
)
            
# --- Target per Query: auctions_with_max_bids ---
add_executable(auctions_with_max_bids auctions_with_max_bids_main.cpp)
target_link_libraries(auctions_with_max_bids PRIVATE Threads::Threads pthread)
