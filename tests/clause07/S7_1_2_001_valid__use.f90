! rule: S7.1.2-001
! covers: use-renamed-derived-name
! evidence: positive-control
module type_basics_export
    implicit none
    private
    type, public :: exported_item
        integer :: payload
    end type exported_item
end module type_basics_export

program type_basics_use
    use type_basics_export, only: local_item => exported_item
    implicit none
    type(local_item) :: value

    value%payload = 31
    if (value%payload /= 31) error stop 1
end program type_basics_use
