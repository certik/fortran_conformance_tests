! rule: S7.4.4.4-002
! covers: digit-order
! evidence: effect
! standard: f2023
program character_type_case
implicit none
character(*), parameter :: alphabet = '0123456789'
integer :: i
if (len(alphabet) /= 10) error stop 1
do i = 1, 9
    if (.not. (alphabet(i:i) < alphabet(i+1:i+1))) error stop 2
end do
end program
