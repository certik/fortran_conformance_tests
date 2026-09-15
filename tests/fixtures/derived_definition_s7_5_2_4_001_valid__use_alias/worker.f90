module worker
use types, only: worker_record => record
implicit none
contains
subroutine change(value)
    type(worker_record), intent(inout) :: value
    type(worker_record) :: local
    local%payload = 17
    if (.not. same_type_as(value,local)) error stop 1
    if (value%payload /= 11) error stop 2
    value%payload = local%payload
end subroutine
end module
