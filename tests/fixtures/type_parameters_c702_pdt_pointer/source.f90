program type_parameters_pdt_pointer
    implicit none
    type :: packet(width)
        integer, len :: width
        character(len=width) :: payload
    end type packet
    type(packet(:)), pointer :: value
end program type_parameters_pdt_pointer
