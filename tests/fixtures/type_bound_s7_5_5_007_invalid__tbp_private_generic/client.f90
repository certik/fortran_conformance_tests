program p
use tbp_provider, only: object
implicit none
integer :: observed
object%payload = 17
observed = object%g()
end program p
