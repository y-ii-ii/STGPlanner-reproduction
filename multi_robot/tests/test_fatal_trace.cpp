#include "utils/fatal_trace.h"
#include <sys/wait.h>
#include <cassert>
#include <string>
#include <iostream>
int main(){
 int pipefd[2];assert(pipe(pipefd)==0);pid_t pid=fork();assert(pid>=0);
 if(pid==0){close(pipefd[0]);dup2(pipefd[1],STDERR_FILENO);assert(utils::installFatalTrace());raise(SIGSEGV);_exit(1);}
 close(pipefd[1]);std::string output;char buf[4096];ssize_t n;
 while((n=read(pipefd[0],buf,sizeof(buf)))>0)output.append(buf,n);
 close(pipefd[0]);int status;assert(waitpid(pid,&status,0)==pid);
 assert(WIFSIGNALED(status)&&WTERMSIG(status)==SIGSEGV);
 assert(output.find("STGPLANNER_FATAL")!=std::string::npos);
 assert(output.find("test_fatal_trace")!=std::string::npos);
 std::cout<<"3 native crash diagnostic checks passed (trace, frames, original SIGSEGV preserved)\n";
}
