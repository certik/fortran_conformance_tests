program ieee_round_constants_core
  use, intrinsic :: ieee_arithmetic, only: ieee_round_type, ieee_nearest, &
    ieee_to_zero, ieee_up, ieee_down, ieee_away, ieee_other, operator(==), operator(/=)
  implicit none
  integer :: checks
  type(ieee_round_type) :: rounds(6)
  logical :: same_round(2), different_round(2)
  checks = 0
  rounds = [ieee_nearest, ieee_to_zero, ieee_up, ieee_down, ieee_away, ieee_other]
  call expect_true(all(rounds(1:5) /= rounds(2:6)), 'round-listed-distinct')
  call expect_true(ieee_other == ieee_other, 'round-other-defined')
  same_round = [ieee_nearest, ieee_up] == [ieee_nearest, ieee_up]
  different_round = [ieee_nearest, ieee_up] /= [ieee_down, ieee_to_zero]
  call expect_true(all(same_round), 'round-elemental-equality')
  call expect_true(all(different_round), 'round-elemental-inequality')
  call expect_count(4)
  write(*,'(a)') 'IEEE 17.1-17.3 ROUND CONSTANTS CORE SUPPORTED OK'
contains
  subroutine expect_true(value, label)
    logical, intent(in) :: value
    character(len=*), intent(in) :: label
    if (.not. value) then
      write(*,'(a,1x,a)') 'IEEE17:false', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_true
  subroutine expect_count(expected)
    integer, intent(in) :: expected
    if (checks /= expected) then
      write(*,'(a)') 'IEEE17:round-count'
      error stop 1
    end if
  end subroutine expect_count
end program ieee_round_constants_core
