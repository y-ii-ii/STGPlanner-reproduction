#pragma once
#include <vector>
#include <queue>
#include <cmath>
#include <limits>
namespace rapid_cover_planner {
struct TeamGridSearch {
 std::vector<double> cost;std::vector<int> parent;
 TeamGridSearch(int nx,int ny,double resolution,const std::vector<bool>&free,int root):cost(nx*ny,INFINITY),parent(nx*ny,-1){
  if(root<0||root>=nx*ny||!free[root])return;
  using Entry=std::pair<double,int>;std::priority_queue<Entry,std::vector<Entry>,std::greater<Entry>> pq;
  cost[root]=0;pq.push({0,root});
  while(!pq.empty()){
   auto e=pq.top();pq.pop();int u=e.second;if(e.first>cost[u]+1e-8)continue;int x=u/ny,y=u%ny;
   for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy){
    int xx=x+dx,yy=y+dy;if((!dx&&!dy)||xx<0||yy<0||xx>=nx||yy>=ny)continue;int v=xx*ny+yy;
    if(!free[v]||(dx&&dy&&(!free[(x+dx)*ny+y]||!free[x*ny+y+dy])))continue;
    double c=cost[u]+resolution*std::hypot(dx,dy);
    if(c+1e-8<cost[v]){cost[v]=c;parent[v]=u;pq.push({c,v});}
   }
  }
 }
 std::vector<int> path(int target)const{
  if(target<0||target>=int(cost.size())||!std::isfinite(cost[target]))return {};
  std::vector<int> out;for(int u=target;u!=-1;u=parent[u])out.push_back(u);
  return std::vector<int>(out.rbegin(),out.rend());
 }
};
}
