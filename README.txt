Pour compiler les libs C LLAMA compatibles avec un R630, utiliser la variable d'environnement :
CMAKE_ARGS="-DLLAMA_AVX2=OFF -DLLAMA_F16C=ON -DLLAMA_FMA=OFF" FORCE_CMAKE=1

Par exemple :
CMAKE_ARGS="-DLLAMA_AVX2=OFF -DLLAMA_F16C=ON -DLLAMA_FMA=OFF" FORCE_CMAKE=1 python3 -m pip --trusted-host pypi.python.org --trusted-host pypi.org --trusted-host files.pythonhosted.org --proxy="proxy.dune.thales:3128" install --upgrade --force-reinstall llama_cpp_python --no-cache-dir
