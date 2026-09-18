program parameter_value_character_padding_effect
  implicit none
  character(len=4) :: word
  parameter (word='AB')
  integer :: visits, returns, observed_checks, main_checks
  visits=0
  returns=0
  observed_checks=0
  main_checks=0
  call observe
  returns=returns+1
  if (visits /= 1) then
    write(*,'(a)') 'PVE:character_padding:observer-visits'
    error stop
  end if
  main_checks=main_checks+1
  if (returns /= 1) then
    write(*,'(a)') 'PVE:character_padding:normal-returns'
    error stop
  end if
  main_checks=main_checks+1
  if (observed_checks /= 6) then
    write(*,'(a)') 'PVE:character_padding:observed-checks'
    error stop
  end if
  main_checks=main_checks+1
  if (main_checks /= 3) then
    write(*,'(a)') 'PVE:character_padding:main-check-total'
    error stop
  end if
  write(*,'(a)') 'PARAMETER VALUES CHARACTER PADDING OK'
contains
  subroutine observe
    implicit none
    visits=visits+1
    if (len(word) /= 4) then
      write(*,'(a)') 'PVE:character_padding:length'
      error stop
    end if
    observed_checks=observed_checks+1
    if (word /= 'AB  ') then
      write(*,'(a)') 'PVE:character_padding:whole-word'
      error stop
    end if
    observed_checks=observed_checks+1
    if (word(1:1) /= 'A') then
      write(*,'(a)') 'PVE:character_padding:position-1'
      error stop
    end if
    observed_checks=observed_checks+1
    if (word(2:2) /= 'B') then
      write(*,'(a)') 'PVE:character_padding:position-2'
      error stop
    end if
    observed_checks=observed_checks+1
    if (word(3:3) /= ' ') then
      write(*,'(a)') 'PVE:character_padding:position-3'
      error stop
    end if
    observed_checks=observed_checks+1
    if (word(4:4) /= ' ') then
      write(*,'(a)') 'PVE:character_padding:position-4'
      error stop
    end if
    observed_checks=observed_checks+1
  end subroutine observe
end program parameter_value_character_padding_effect
