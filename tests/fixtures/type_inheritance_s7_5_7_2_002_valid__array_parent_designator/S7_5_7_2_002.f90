program p
implicit none
type :: parent
    integer :: payload
end type
type, extends(parent) :: child
    integer :: marker
end type
type(child) :: objects(2)
objects%payload = [17,19]
objects%marker = [41,43]
if (rank(objects%parent) /= 1) error stop 1
if (rank(objects(1)%parent) /= 0) error stop 2
if (any(objects%parent%payload /= [17,19])) error stop 3
if (any(objects%marker /= [41,43])) error stop 4
end program p
