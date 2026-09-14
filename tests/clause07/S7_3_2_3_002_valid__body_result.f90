! rule: S7.3.2.3-002
! covers: body-local-polymorphic-result
! evidence: effect
program class_body_result
    implicit none
    class(*), allocatable :: value
    integer :: status = -1, seen = -1
    allocate(value, source=make(seen), stat=status)
    if (status /= 0) error stop 'caller-allocation'
    if (.not. allocated(value)) error stop 'caller-unallocated'
    if (rank(value) /= 0) error stop 'caller-result-rank'
    if (seen /= 53) error stop 'function-body-not-observed'
    deallocate(value)
contains
    class(local_root) function make(observed) result(r)
        type :: local_root
            integer :: tag
        end type
        type, extends(local_root) :: local_child
            integer :: extra
        end type
        allocatable :: r
        integer, intent(out) :: observed
        integer :: ios
        observed = -1
        ios = -1
        allocate(local_child :: r, stat=ios)
        if (ios /= 0) error stop 'result-allocation'
        if (.not. allocated(r)) error stop 'result-unallocated'
        select type (r)
        type is (local_child)
            r%tag = 17
            r%extra = 36
            if (r%tag /= 17) error stop 'local-root-payload'
            if (r%extra /= 36) error stop 'local-child-payload'
            observed = r%tag + r%extra
        class default
            error stop 'local-result-dynamic-type'
        end select
    end function
end program
