program p
implicit none
type :: parent(k,n)
    integer, kind :: k
    integer, len :: n
    integer :: payload
end type
type, extends(parent) :: child(m)
    integer, len :: m
    integer :: marker
end type
type(child(k=2,n=3,m=5)) :: object
object%payload = 17
object%marker = 41
if (object%parent%k /= 2) error stop 1
if (object%parent%n /= 3) error stop 2
if (object%m /= 5) error stop 3
if (object%parent%payload /= 17) error stop 4
if (object%marker /= 41) error stop 5
end program p
