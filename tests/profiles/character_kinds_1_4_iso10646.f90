program character_kinds_1_4_iso10646
    use iso_fortran_env, only: character_kinds
    implicit none
    if (.not. any(character_kinds == 1)) stop 77
    if (.not. any(character_kinds == 4)) stop 77
    if (selected_char_kind('ISO_10646') /= 4) stop 77
end program
