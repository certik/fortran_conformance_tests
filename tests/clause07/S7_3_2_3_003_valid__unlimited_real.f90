! rule: S7.3.2.3-003
! covers: unlimited-real-kinds
! evidence: effect
program dynamic_unlimited_real
    implicit none
    integer, parameter :: default_kind = kind(0.0), double_kind = kind(0.0d0)
    class(*), allocatable :: value
    integer :: status = -1
    allocate(real(kind=default_kind) :: value, stat=status)
    if (status /= 0) error stop 'default-allocation'
    if (.not. allocated(value)) error stop 'default-unallocated'
    select type (value)
    type is (real(kind=default_kind))
        value = 0.0_default_kind
        if (kind(value) /= default_kind) error stop 'default-kind'
        if (value /= 0.0_default_kind) error stop 'default-value'
    class default
        error stop 'default-type-kind'
    end select
    deallocate(value)
    status = -1
    allocate(real(kind=double_kind) :: value, stat=status)
    if (status /= 0) error stop 'double-allocation'
    if (.not. allocated(value)) error stop 'double-unallocated'
    select type (value)
    type is (real(kind=double_kind))
        value = 0.0_double_kind
        if (kind(value) /= double_kind) error stop 'double-kind'
        if (value /= 0.0_double_kind) error stop 'double-value'
    class default
        error stop 'double-type-kind'
    end select
    deallocate(value)
end program
