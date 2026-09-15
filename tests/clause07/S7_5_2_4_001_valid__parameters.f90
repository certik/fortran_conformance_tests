! rule: S7.5.2.4-001
! covers: parameter-values-not-type-identity
! evidence: effect
! standard: f2023
program p
implicit none
type :: record(k,n)
    integer, kind :: k
    integer, len :: n
    integer :: payload(n)
end type
type(record(1,2)) :: a
type(record(2,3)) :: b
a%payload = [11,13]
b%payload = [17,19,23]
if (a%k /= 1 .or. a%n /= 2) error stop 1
if (b%k /= 2 .or. b%n /= 3) error stop 2
if (.not. same_type_as(a,b)) error stop 3
if (any(a%payload /= [11,13])) error stop 4
if (any(b%payload /= [17,19,23])) error stop 5
end program
