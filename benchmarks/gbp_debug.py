from pathlib import Path
p=Path('/opt/stgplanner/benchmarks/gbp2_ws/src/gbplanner/src/rrg.cpp')
s=p.read_text()
if 'BENCHMARK_DIAGNOSTICS' not in s:
    marker='\n// BENCHMARK_DIAGNOSTICS: enable existing native graph/ground diagnostics.\n#undef global_verbosity\n#define global_verbosity Verbosity::DEBUG\n'
    # After include directives, before the first method body.
    pos=s.index('Rrg::Rrg(');s=s[:pos]+marker+s[pos:];p.write_text(s)
print('Enabled native GBP2 graph diagnostics')
