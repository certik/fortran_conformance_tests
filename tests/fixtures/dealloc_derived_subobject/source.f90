! rule: S9.7.3.2-010
! covers: derived-deallocation-deallocates-allocatable-subobject
! Parent and component allocation are proved before DEALLOCATE; component deallocation is observed only by finalizer log.
module dealloc_derived_subobject_log
  implicit none
  private
  integer, parameter :: capacity = 8
  integer, save :: nlog = 0
  integer, save :: log_value(capacity) = -1
  public :: reset_log, record_log, expect_log
contains
  subroutine reset_log()
    nlog = 0
    log_value = -1
  end subroutine reset_log

  subroutine record_log(value)
    integer, intent(in) :: value
    if (nlog >= capacity) error stop 'D9732:derived-subobject:log-capacity'
    nlog = nlog + 1
    log_value(nlog) = value
  end subroutine record_log

  subroutine expect_log(expected)
    integer, intent(in) :: expected(:)
    if (nlog /= size(expected)) error stop 'D9732:derived-subobject:log-count'
    if (any(log_value(1:nlog) /= expected)) error stop 'D9732:derived-subobject:log-values'
  end subroutine expect_log
end module dealloc_derived_subobject_log

module dealloc_derived_subobject_types
  use dealloc_derived_subobject_log, only: record_log
  implicit none
  private
  public :: leaf, owner
  type :: leaf
    integer :: token = -1
  contains
    final :: finish_leaf_vector
  end type leaf
  type :: owner
    integer :: tag = -1
    type(leaf), allocatable :: part(:)
  end type owner
contains
  subroutine finish_leaf_vector(x)
    type(leaf), intent(inout) :: x(:)
    integer :: i
    call record_log(size(x))
    do i = 1, size(x)
      call record_log(x(i)%token)
    end do
  end subroutine finish_leaf_vector
end module dealloc_derived_subobject_types

program dealloc_derived_subobject
  use dealloc_derived_subobject_log, only: reset_log, expect_log
  use dealloc_derived_subobject_types, only: owner
  implicit none
  type(owner), allocatable :: item
  integer :: stat, checks
  checks = 0
  call reset_log()

  allocate(item, stat=stat)
  if (stat /= 0) error stop 'D9732:derived-subobject:parent-allocate-stat'
  allocate(item%part(-11:-9), stat=stat)
  if (stat /= 0) error stop 'D9732:derived-subobject:component-allocate-stat'
  item%tag = 359
  item%part%token = [367, 373, 379]
  if (.not. allocated(item)) error stop 'D9732:derived-subobject:before-parent-allocated'
  checks = checks + 1
  if (.not. allocated(item%part)) error stop 'D9732:derived-subobject:before-component-allocated'
  checks = checks + 1
  if (lbound(item%part,1) /= -11) error stop 'D9732:derived-subobject:before-lower'
  checks = checks + 1
  if (ubound(item%part,1) /= -9) error stop 'D9732:derived-subobject:before-upper'
  checks = checks + 1
  if (item%tag /= 359) error stop 'D9732:derived-subobject:before-tag'
  checks = checks + 1
  if (any(item%part%token /= [367, 373, 379])) error stop 'D9732:derived-subobject:before-values'
  checks = checks + 1

  deallocate(item, stat=stat)
  if (stat /= 0) error stop 'D9732:derived-subobject:deallocate-stat'
  checks = checks + 1
  if (allocated(item)) error stop 'D9732:derived-subobject:after-parent-unallocated'
  checks = checks + 1
  call expect_log([3, 367, 373, 379])
  checks = checks + 1

  if (checks /= 9) error stop 'D9732:derived-subobject:check-total'
  write(*,'(a)') 'DEALLOC DERIVED SUBOBJECT OK'
end program dealloc_derived_subobject
