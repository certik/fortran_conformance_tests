program type_parameters_pdt_pair
    implicit none
    type :: packet(width)
        integer, len :: width
        character(len=width) :: payload
    end type packet
    type(packet(:)), allocatable :: value
end program type_parameters_pdt_pair
