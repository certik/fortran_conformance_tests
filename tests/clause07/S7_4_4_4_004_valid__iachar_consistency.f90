! rule: S7.4.4.4-004
! covers: iachar-consistency
! evidence: effect
! standard: f2023
program character_type_case
implicit none
character(*), parameter :: sample = 'OTX'
integer :: i, j
do i = 1, 3
    if (achar(iachar(sample(i:i))) /= sample(i:i)) error stop 1
    do j = 1, 3
        if (lle(sample(i:i),sample(j:j))) then
            if (iachar(sample(i:i)) > iachar(sample(j:j))) error stop 2
        end if
    end do
end do
end program
