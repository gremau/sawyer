CREATE TABLE quality_flags (
  logger TEXT NOT NULL, 
  flagnum INTEGER NOT NULL, 
  varname TEXT NOT NULL,
  q_func TEXT NOT NULL,
  q_func_arg1 TEXT,
  q_func_arg2 TEXT,
  q_func_arg3 TEXT,
  q_func_arg4 TEXT,
  q_func_arg5 TEXT,
  startflag DATETIME,
  endflag DATETIME,
  description TEXT,
  PRIMARY KEY (logger, flagnum, varname)
); 

CREATE TABLE gap_flags (
  logger TEXT NOT NULL, 
  flagnum INTEGER NOT NULL, 
  varname TEXT NOT NULL,
  src_level TEXT,
  src_varname TEXT,
  gf_func TEXT NOT NULL,
  startflag DATETIME,
  endflag DATETIME,
  startfit DATETIME,
  endfit DATETIME,
  gf_kwargs TEXT,
  description TEXT,
  PRIMARY KEY (logger, flagnum, varname)
); 