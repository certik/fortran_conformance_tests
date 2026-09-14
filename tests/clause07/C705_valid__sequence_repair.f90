! rule: C705
! covers: extensible
! evidence: positive-control
program c705_sequence
    implicit none
    type :: record
        integer :: code
    end type
    class(record), pointer :: value => null()
    if (associated(value)) error stop 'association'
end program
