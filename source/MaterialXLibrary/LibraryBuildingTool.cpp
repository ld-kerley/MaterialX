//
// Created by Lee Kerley on 2/12/25.
//

#include <string>
#include <sstream>
#include <fstream>
#include <iostream>

using namespace std;

int main(int argc, char** argv)
{
    string sourceFilename = argv[1];
    string destFilename = argv[2];

    cout << "Copying '" << sourceFilename << "' to '" << destFilename << "'" << std::endl;

    std::ifstream t(sourceFilename);
    std::stringstream buffer;
    buffer << t.rdbuf();

    std::ofstream ofs(destFilename);
    ofs << buffer.str();

    return 0;

}