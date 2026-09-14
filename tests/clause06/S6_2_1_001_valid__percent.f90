! rule: S6.2.1-001
! covers: percent
! evidence: positive-control
program token_percent_admission
    implicit none
    type :: box
        integer :: value
    end type box
    type(box) :: object

    object%value = 19
    if (object%value /= 19) error stop 1
end program token_percent_admission
