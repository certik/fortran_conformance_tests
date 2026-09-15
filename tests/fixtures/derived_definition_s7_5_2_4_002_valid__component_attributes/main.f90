program p
use types_a, only: a_record => record
use types_b, only: b_record => record
use dispatch, only: identify
use iso_c_binding, only: c_int
implicit none
type(a_record) :: a
type(b_record) :: b
integer, target :: target(2)
integer :: stat
target=[11,13]
a%payload=>target
allocate(b%payload(2),stat=stat)
if (stat/=0) error stop 7
if (.not. allocated(b%payload)) error stop 8
b%payload=[17,19]
if (identify(a) /= 1) error stop 1
if (identify(b) /= 2) error stop 2
end program
