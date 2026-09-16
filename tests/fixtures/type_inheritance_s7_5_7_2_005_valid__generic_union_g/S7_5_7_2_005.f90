program p
use generic_types, only: child, overriding_child, separate_child
implicit none
type(child) :: a
type(overriding_child) :: b
type(separate_child) :: c
integer :: observed
a%payload = 17
a%marker = 31
b%payload = 17
b%marker = 41
c%payload = 17
c%marker = 43
observed = a%g(1)
if (observed /= 11) error stop 1
observed = a%g(1.0)
if (observed /= 22) error stop 2
observed = b%g(1)
if (observed /= 33) error stop 3
observed = b%g(1.0)
if (observed /= 22) error stop 4
observed = c%g(1)
if (observed /= 11) error stop 5
observed = c%h(1.0)
if (observed /= 22) error stop 6
end program
