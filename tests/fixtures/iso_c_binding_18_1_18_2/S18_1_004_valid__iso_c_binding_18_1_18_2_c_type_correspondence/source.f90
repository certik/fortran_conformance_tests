! rule: S18.1-004
! covers: iso-c-binding-kind-constants derived-types-correspond-to-c-types
! evidence: effect
! standard: f2023
! oracle-basis: standard
program iso_c_binding_c_type_correspondence
  use, intrinsic :: iso_c_binding, only: c_int
  implicit none
  type, bind(c) :: pair
    integer(c_int) :: left
    integer(c_int) :: right
  end type
  interface
    integer(c_int) function c_int_identity(value) bind(c, name="batch310_int_identity")
      import c_int
      integer(c_int), value :: value
    end function
    integer(c_int) function c_pair_sum(value) bind(c, name="batch310_pair_sum")
      import c_int, pair
      type(pair), value :: value
    end function
  end interface
  type(pair) :: item
  integer(c_int) :: checks
  checks = 0_c_int
  item%left = 17_c_int
  item%right = 25_c_int
  call expect_int(c_int_identity(55_c_int), 55_c_int, 'C_INT corresponding C int')
  call expect_int(c_pair_sum(item), 42_c_int, 'BIND(C) derived type corresponding struct')
  call expect_int(checks, 2_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.1 C TYPE CORRESPONDENCE OK'

contains
  subroutine expect_int(actual, expected, label)
    integer(c_int), intent(in) :: actual, expected
    character(len=*), intent(in) :: label
    if (actual /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ISO-C-BINDING-CHECK-FAIL', label, actual, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_logical(actual, expected, label)
    logical, intent(in) :: actual, expected
    character(len=*), intent(in) :: label
    if (actual .neqv. expected) then
      write(*,'(a,1x,a,1x,l1,1x,l1)') 'ISO-C-BINDING-CHECK-FAIL', label, actual, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
end program
