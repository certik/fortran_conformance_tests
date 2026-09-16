program p
use tbp_provider, only: object, prepare
implicit none
integer :: observed
call prepare()
observed = object%get()
if (observed /= 17) error stop 1
end program p
