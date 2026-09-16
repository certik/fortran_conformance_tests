submodule(access_provider) access_child
contains
module procedure fill
  item%hidden=7
end procedure
module procedure read_value
  read_value=item%hidden
end procedure
end submodule
