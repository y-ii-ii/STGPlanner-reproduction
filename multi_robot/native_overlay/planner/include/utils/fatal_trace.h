#pragma once
#include <execinfo.h>
#include <signal.h>
#include <unistd.h>
namespace utils {
// Diagnostic only: preserve SIGSEGV termination, never resume invalid planner
// state. Unwinding after corruption is best effort, not a crash repair. The
// independent velocity gates remain the physical stop authority.
inline void fatalTrace(int signo,siginfo_t*,void*){
 const char text[]="STGPLANNER_FATAL native stack (best effort)\n";
 const ssize_t written=::write(STDERR_FILENO,text,sizeof(text)-1);(void)written;
 void* frames[48];int count=::backtrace(frames,48);::backtrace_symbols_fd(frames,count,STDERR_FILENO);
 sigset_t set;sigemptyset(&set);sigaddset(&set,signo);sigprocmask(SIG_UNBLOCK,&set,nullptr);
 ::kill(::getpid(),signo);::_exit(128+signo);
}
inline bool installFatalTrace(){
 static char alternate[64*1024];stack_t stack{};stack.ss_sp=alternate;stack.ss_size=sizeof(alternate);
 if(sigaltstack(&stack,nullptr)!=0)return false;
 void* warm[1];::backtrace(warm,1);
 struct sigaction action{};action.sa_sigaction=&fatalTrace;sigemptyset(&action.sa_mask);
 action.sa_flags=SA_SIGINFO|SA_ONSTACK|SA_RESETHAND;
 return sigaction(SIGSEGV,&action,nullptr)==0;
}
}
