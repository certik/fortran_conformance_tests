program ieee_relational_invalid_table
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks
  logical :: relation
  real, volatile :: qnan, one
  checks = 0
  one = 1.0
  qnan = ieee_value(one, ieee_quiet_nan)
  call prepare(ieee_invalid)
  relation = qnan < one
  call expect_relation(relation, .false., ieee_invalid, .true., 'lt-symbolic')
  call prepare(ieee_invalid)
  relation = qnan .le. one
  call expect_relation(relation, .false., ieee_invalid, .true., 'le-dotted')
  call prepare(ieee_invalid)
  relation = qnan > one
  call expect_relation(relation, .false., ieee_invalid, .true., 'gt-symbolic')
  call prepare(ieee_invalid)
  relation = qnan .ge. one
  call expect_relation(relation, .false., ieee_invalid, .true., 'ge-dotted')
  call prepare(ieee_invalid)
  relation = qnan == one
  call expect_relation(relation, .false., ieee_invalid, .false., 'eq-symbolic')
  call prepare(ieee_invalid)
  relation = qnan .ne. one
  call expect_relation(relation, .true., ieee_invalid, .false., 'ne-dotted')
  call expect_count(6)
  write(*,'(a)') 'IEEE 17.1-17.3 RELATIONAL INVALID TABLE SUPPORTED OK'
contains

          subroutine prepare(flag)
            type(ieee_flag_type), intent(in) :: flag
            logical :: halting
            if (.not. ieee_support_flag(flag, 0.0)) error stop 77
            if (ieee_support_halting(flag)) then
              call ieee_set_halting_mode(flag, .false.)
            else
              call ieee_get_halting_mode(flag, halting)
              if (halting) error stop 77
            end if
            call ieee_set_flag(flag, .false.)
          end subroutine prepare
    subroutine expect_relation(value, expected, flag, flag_expected, label)
  logical, intent(in) :: value, expected, flag_expected
  type(ieee_flag_type), intent(in) :: flag
  character(len=*), intent(in) :: label
  if (value .neqv. expected) then
    write(*,'(a,1x,a)') 'IEEE17:relation', label
    error stop 1
  end if
  call expect_flag(flag, flag_expected, label)
end subroutine expect_relation

          subroutine expect_true(value, label)
            logical, intent(in) :: value
            character(len=*), intent(in) :: label
            if (.not. value) then
              write(*,'(a,1x,a)') 'IEEE17:true', label
              error stop 1
            end if
            checks = checks + 1
          end subroutine expect_true
          subroutine expect_false(value, label)
            logical, intent(in) :: value
            character(len=*), intent(in) :: label
            if (value) then
              write(*,'(a,1x,a)') 'IEEE17:false', label
              error stop 1
            end if
            checks = checks + 1
          end subroutine expect_false
          subroutine expect_flag(flag, expected, label)
            type(ieee_flag_type), intent(in) :: flag
            logical, intent(in) :: expected
            character(len=*), intent(in) :: label
            logical :: observed
            call ieee_get_flag(flag, observed)
            if (observed .neqv. expected) then
              write(*,'(a,1x,a)') 'IEEE17:flag', label
              error stop 1
            end if
            checks = checks + 1
          end subroutine expect_flag
          subroutine expect_count(expected)
            integer, intent(in) :: expected
            if (checks /= expected) then
              write(*,'(a)') 'IEEE17:relational-count'
              error stop 1
            end if
          end subroutine expect_count
    end program ieee_relational_invalid_table
