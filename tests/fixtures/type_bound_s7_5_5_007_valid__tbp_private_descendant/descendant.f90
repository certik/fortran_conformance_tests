submodule(tbp_provider) tbp_descendant
implicit none
contains
module procedure inspect
integer :: observed
object%payload = 17
observed = object%secret()
end procedure inspect
end submodule tbp_descendant
