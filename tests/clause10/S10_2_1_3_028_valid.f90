! rule: S10.2.1.3-028
! covers: both-unallocated
! evidence: positive-control
! requires: coarray
! F2023 10.2.1.3 p15: the mismatched allocation state is not executed.
program s10_2_1_3_028_valid
    implicit none
    type :: packet
        integer :: payload
        integer, allocatable :: values(:)[:]
    end type
    type(packet), save :: source, copy
    source%payload = 17
    copy%payload = -1
    if (allocated(source%values) .or. allocated(copy%values)) error stop 'initial-state'
    copy = source
    if (copy%payload /= 17) error stop 'ordinary-component'
    if (allocated(copy%values)) error stop 'both-unallocated'
    if (allocated(source%values)) error stop 'source-unchanged'
end program
