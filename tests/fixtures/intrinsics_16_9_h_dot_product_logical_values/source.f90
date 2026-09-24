! rule: S16.9.73-005
! covers: DOT_PRODUCT-logical-any-and
! covers: DOT_PRODUCT-logical-zero-size-false
program i169h_dot_product_logical_values
  implicit none
  integer :: checks
  logical :: za(0), zb(0)
  checks = 0
  call require('DOT_PRODUCT logical is ANY of aligned AND values', &
       dot_product([.true., .false.], [.true., .true.]) .and. &
       .not. dot_product([.true., .false.], [.false., .true.]), checks)
  call require('DOT_PRODUCT zero-size logical vectors false with true companion', &
       .not. dot_product(za, zb) .and. dot_product([.true.], [.true.]), checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DOT PRODUCT LOGICAL VALUES OK'
contains
  subroutine require(label, condition, checks)
    character(len=*), intent(in) :: label
    logical, intent(in) :: condition
    integer, intent(inout) :: checks
    if (.not. condition) then
      write(*,'(a)') label
      error stop
    end if
    checks = checks + 1
  end subroutine require
end program i169h_dot_product_logical_values
