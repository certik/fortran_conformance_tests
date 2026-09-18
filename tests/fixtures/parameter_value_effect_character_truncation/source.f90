program parameter_value_character_truncation_effect
  implicit none
  character(len=2) :: word
  character(len=*) :: full_word
  parameter (word='ABCDE', full_word='CDE')
  integer :: visits, returns, observed_checks, main_checks
  visits=0
  returns=0
  observed_checks=0
  main_checks=0
  call observe
  returns=returns+1
  if (visits /= 1) then
    write(*,'(a)') 'PVE:character_truncation:observer-visits'
    error stop
  end if
  main_checks=main_checks+1
  if (returns /= 1) then
    write(*,'(a)') 'PVE:character_truncation:normal-returns'
    error stop
  end if
  main_checks=main_checks+1
  if (observed_checks /= 6) then
    write(*,'(a)') 'PVE:character_truncation:observed-checks'
    error stop
  end if
  main_checks=main_checks+1
  if (main_checks /= 3) then
    write(*,'(a)') 'PVE:character_truncation:main-check-total'
    error stop
  end if
  write(*,'(a)') 'PARAMETER VALUES CHARACTER TRUNCATION OK'
contains
  subroutine observe
    implicit none
    visits=visits+1
    if (len(word) /= 2) then
      write(*,'(a)') 'PVE:character_truncation:length'
      error stop
    end if
    observed_checks=observed_checks+1
    if (word /= 'AB') then
      write(*,'(a)') 'PVE:character_truncation:whole-word'
      error stop
    end if
    observed_checks=observed_checks+1
    if (word(1:1) /= 'A') then
      write(*,'(a)') 'PVE:character_truncation:position-1'
      error stop
    end if
    observed_checks=observed_checks+1
    if (word(2:2) /= 'B') then
      write(*,'(a)') 'PVE:character_truncation:position-2'
      error stop
    end if
    observed_checks=observed_checks+1
    if (len(full_word) /= 3) then
      write(*,'(a)') 'PVE:character_truncation:assumed-length'
      error stop
    end if
    observed_checks=observed_checks+1
    if (full_word /= 'CDE') then
      write(*,'(a)') 'PVE:character_truncation:assumed-value'
      error stop
    end if
    observed_checks=observed_checks+1
  end subroutine observe
end program parameter_value_character_truncation_effect
