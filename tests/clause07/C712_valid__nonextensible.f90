! rule: C712
! covers: nonextensible-data-ref
! evidence: positive-control
! standard: f2023
program c712_nonextensible
    implicit none
    type :: record
        sequence
        integer :: code
    end type
    type(record) :: seed = record(3)
    classof(seed), allocatable :: copy
end program
