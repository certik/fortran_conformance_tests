submodule(root:first) second
implicit none
contains
module procedure inspect
    type(hidden_record) :: value
    value = hidden_record(17)
    tag = value%payload
end procedure
end submodule
