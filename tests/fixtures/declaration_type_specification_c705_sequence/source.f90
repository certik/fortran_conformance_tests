program c705_sequence
    implicit none
    type :: record
        sequence
        integer :: code
    end type
    class(record), pointer :: value => null()
    if (associated(value)) error stop 'association'
end program
