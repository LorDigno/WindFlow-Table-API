
cmake_minimum_required(VERSION 3.16)
project(WindFlowGeneratedQueries CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -DNDEBUG")

find_package(Threads REQUIRED)

include_directories(
    "/disc1/homes/lorenzoni/WindFlow-Table-API/nexmark_queries/../include"
    "/disc1/homes/lorenzoni/WindFlow-Table-API/nexmark_queries/../include/WindFlow/wf"
    "/disc1/homes/lorenzoni/WindFlow-Table-API/nexmark_queries/../include/fastflow"
    "/disc1/homes/lorenzoni/WindFlow-Table-API/nexmark_queries/../include/Table_WindFlow"
    "/disc1/homes/lorenzoni/WindFlow-Table-API/nexmark_queries/query6"
)
            
# --- Target per Query: avg_selling_price_by_seller ---
add_executable(avg_selling_price_by_seller avg_selling_price_by_seller_main.cpp)
target_link_libraries(avg_selling_price_by_seller PRIVATE Threads::Threads pthread)
