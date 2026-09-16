program p
use extension, only: object, initialize
implicit none
integer :: observed
call initialize()
observed = object%alias%payload
if (observed /= 17) error stop 1
end program
