! rule: S16.9.100-003
! covers: IAND-boz-converted-as-int-to-other-kind
program i169l_iand_boz_conversion
  implicit none
  interface type_code
    procedure type_code_integer, type_code_real
  end interface
  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)
  integer :: checks, k
  integer(kind=ik) :: v
  checks = 0
  v = int(z'0A', kind=ik)
  call require('IAND converts BOZ as INT to other kind', &
       all([(btest(iand(z'0F', v), k) .eqv. &
              btest(iand(int(z'0F', kind=ik), v), k), k = 0, 4)]), checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 L IAND BOZ CONVERSION OK'
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
  integer function type_code_integer(x)
    integer, intent(in) :: x
    type_code_integer = 1
  end function type_code_integer
  integer function type_code_real(x)
    real, intent(in) :: x
    type_code_real = 2
  end function type_code_real
end program i169l_iand_boz_conversion
