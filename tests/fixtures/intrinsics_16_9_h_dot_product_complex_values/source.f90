! rule: S16.9.73-004
! covers: DOT_PRODUCT-complex-conjugated-sum
! covers: DOT_PRODUCT-complex-zero-size-zero
program i169h_dot_product_complex_values
  implicit none
  integer :: checks
  complex :: ca(1), cb(1), za(0), zb(0), got
  checks = 0
  ca = [cmplx(1.0, 2.0)]; cb = [cmplx(3.0, 4.0)]
  got = dot_product(ca, cb)
  call require('DOT_PRODUCT complex conjugates VECTOR_A', real(got) == 11.0 .and. aimag(got) == -2.0, checks)
  call require('DOT_PRODUCT zero-size complex vectors give zero with nonzero companion', &
       dot_product(za, zb) == (0.0, 0.0) .and. dot_product(ca, cb) /= (0.0, 0.0), checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DOT PRODUCT COMPLEX VALUES OK'
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
end program i169h_dot_product_complex_values
