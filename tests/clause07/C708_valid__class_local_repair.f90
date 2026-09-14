! rule: C708
! covers: class-allocatable
! evidence: positive-control
program c708_class_local
    implicit none
    type :: payload
        integer :: code
    end type
    class(payload), allocatable :: value
end program
