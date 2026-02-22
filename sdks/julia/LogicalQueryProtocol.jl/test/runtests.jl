using LogicalQueryProtocol
using ReTestItems
worker_init_expr = :(using Logging; Logging.catch_exceptions(::Any) = false)
runtests(LogicalQueryProtocol; worker_init_expr, nworkers=1)
