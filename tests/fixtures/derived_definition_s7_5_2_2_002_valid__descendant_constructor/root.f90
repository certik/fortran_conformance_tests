module root
implicit none
private
public :: inspect
type :: hidden_record
    integer :: payload
end type
interface
    module subroutine inspect(tag)
        integer, intent(out) :: tag
    end subroutine
end interface
end module
