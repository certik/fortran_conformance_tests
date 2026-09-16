program p
use tbp_child, only: child_object
implicit none
integer :: observed
child_object%payload = 17
child_object%marker = 29
observed = child_object%secret()
end program p
