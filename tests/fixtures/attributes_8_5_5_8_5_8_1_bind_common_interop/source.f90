module attributes_bind_common_mod
  use iso_c_binding, only: c_int
  implicit none
  integer(c_int) :: common_first, common_second
  common /fortran_common_pair/ common_first, common_second
  bind(c, name="attr_bind_common") :: /fortran_common_pair/
  interface
    subroutine c_set_common(a, b) bind(c, name="c_set_common")
      import c_int
      integer(c_int), value :: a, b
    end subroutine
    subroutine c_get_common(a, b) bind(c, name="c_get_common")
      import c_int
      integer(c_int), intent(out) :: a, b
    end subroutine
  end interface
end module attributes_bind_common_mod
program attributes_bind_common_interop
  use iso_c_binding, only: c_int
  use attributes_bind_common_mod
  implicit none
  integer(c_int) :: left_seen, right_seen
  integer :: checks
  checks = 0
  call c_set_common(41_c_int, 43_c_int)
  call expect_equal(int(common_first), 41, 'common first C write')
  call expect_equal(int(common_second), 43, 'common second C write')
  common_first = 47_c_int
  common_second = 53_c_int
  call c_get_common(left_seen, right_seen)
  call expect_equal(int(left_seen), 47, 'common first Fortran write')
  call expect_equal(int(right_seen), 53, 'common second Fortran write')
  call expect_equal(checks, 4, 'check total before completion')
  write(*,'(a)') 'ATTRIBUTES BIND COMMON INTEROP OK'
contains
  subroutine expect_equal(observed, expected, label)
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ATTR-BIND-COMMON-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
end program attributes_bind_common_interop
