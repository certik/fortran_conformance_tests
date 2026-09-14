program c708_classof_local
    implicit none
    type :: payload
        integer :: code
    end type
    type(payload) :: seed = payload(3)
    classof(seed) :: value
end program
